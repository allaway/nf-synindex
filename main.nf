#!/usr/bin/env nextflow


/*
========================================================================================
    SETUP PARAMS
========================================================================================
*/

// Default values
params.outdir = false
params.parent_id = false
params.synapse_config = false

if ( !params.outdir ) {
  exit 1, "Parameter 'params.outdir' is required!\n"
}

if ( !params.parent_id ) {
  exit 1, "Parameter 'params.parent_id' is required!\n"
}

matches = ( params.outdir =~ 's3://([^/]+-tower-bucket)/.*[^*]' ).findAll()

if ( matches.size() == 0 ) {
  exit 1, "Parameter 'params.outdir' must be an S3 prefix URI for a Tower bucket (e.g., 's3://<stack-name>-tower-bucket)/prefix/to/outdir/')!\n"
}

if ( !params.parent_id ==~ 'syn[0-9]+' ) {
  exit 1, "Parameter 'params.parent_id' must be the Synapse ID of a folder (e.g., 'syn98765432')!\n"
}

bucket_name = matches[0][1]
outdir = params.outdir.replaceAll('(/|[^/])$', '/') // Ensure trailing slash
ch_synapse_config = params.synapse_config ? Channel.value( file(params.synapse_config) ) : "null"


/*
========================================================================================
    SETUP PROCESSES
========================================================================================
*/

process get_user_id {
  
  label 'synapse'

  secret 'SYNAPSE_AUTH_TOKEN'

  afterScript "rm -f ${syn_config}"

  input:
  file  syn_config    from ch_synapse_config

  output:
  stdout ch_user_id

  script:
  syn_params = params.synapse_config ? "configPath='${syn_config}'" : ""
  """
  #!/usr/bin/env python3

  import synapseclient

  syn = synapseclient.Synapse(${syn_params})
  syn.login(silent=True)

  user = syn.getUserProfile()
  print(user.ownerId)
  """

}


process update_owner {
  
  label 'aws'

  input:
  val user_id   from ch_user_id
  val bucket    from bucket_name

  output:
  val true    into ch_update_owner_done

  script:
  """
  ( \
     ( aws s3 cp s3://${bucket}/owner.txt - 2>/dev/null || true ); \
      echo $user_id \
  ) \
  | sort -u \
  | aws s3 cp - s3://${bucket}/owner.txt
  """

}


process register_storage_location {
  
  label 'synapse'

  secret 'SYNAPSE_AUTH_TOKEN'

  afterScript "rm -f ${syn_config}"

  input:
  val   bucket        from bucket_name
  file  syn_config    from ch_synapse_config
  val   flag          from ch_update_owner_done

  output:
  stdout ch_storage_id

  script:
  syn_params = params.synapse_config ? "configPath='${syn_config}'" : ""
  """
  #!/usr/bin/env python3

  import json
  import synapseclient
  
  syn = synapseclient.Synapse(${syn_params})
  syn.login(silent=True)

  destination = {
      "uploadType": "S3",
      "concreteType": "org.sagebionetworks.repo.model.project.ExternalS3StorageLocationSetting",
      "bucket": "${bucket}",
  }
  destination = syn.restPOST("/storageLocation", body=json.dumps(destination))
  print(destination['storageLocationId'])
  """

}


process list_objects {

  label 'aws'

  input:
  val outdir    from params.outdir
  val bucket    from bucket_name

  output:
  path 'objects.txt'    into ch_objects

  script:
  """
  aws s3 ls ${outdir} --recursive \
  | grep -v '/\$' \
  | awk 'BEGIN {OFS=""} {\$1=\$2=\$3=""; print "s3://${bucket}/" \$4}' \
  > objects.txt
  """
  
}


process synapse_mirror {
  
  label 'synapse'

  secret 'SYNAPSE_AUTH_TOKEN'

  afterScript "rm -f ${syn_config}"

  input:
  path  objects       from ch_objects
  val   outdir        from params.outdir
  val   parent_id     from params.parent_id
  file  syn_config    from ch_synapse_config

  output:
  path  'folder_ids.csv'    into ch_folder_ids_csv

  script:
  config_param = params.synapse_config ? "--config ${syn_config}" : ""
  """
  synmirror.py \
  --objects ${objects} \
  --outdir ${outdir} \
  --parent_id ${parent_id} \
  ${config_param} \
  > folder_ids.csv
  """

}

// Parse list of object URIs and their Synapse parents
ch_folder_ids_csv
  .text
  .splitCsv()
  .map { row -> [ row[0], file(row[0]), row[1] ] }
  .set { ch_folder_ids }


process synapse_index {
  
  label 'synapse'

  secret 'SYNAPSE_AUTH_TOKEN'

  afterScript "rm -f ${syn_config}"

  input:
  tuple val(uri), file(object), val(parent_id)    from ch_folder_ids
  val   storage_id                                from ch_storage_id
  file  syn_config                                from ch_synapse_config

  output:
  stdout ch_file_ids

  script:
  config_param = params.synapse_config ? "--config ${syn_config}" : ""
  """
  synindex.py \
  --storage_id ${storage_id} \
  --file ${object} \
  --uri ${uri} \
  --parent_id ${parent_id} \
  ${config_param}
  """

}


process output_file_ids {

  input:
  val file_ids    from ch_file_ids.collect()

  output:
  path 'file_ids.csv'     into ch_file_ids_csv

  script:
  """
  echo ${file_ids} > file_ids.csv
  """

}
