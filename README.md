# nf-synindex: Index S3 Objects in Synapse

## Purpose

The purpose of this Nextflow workflow is to automate the process of indexing S3 objects in Synapse. These S3 objects are typically the output files from a general-purpose (_e.g._ nf-core) workflow that doesn't contain Synapse-specific steps for uploading or indexing outputs. This workflow is intended to be run after other data processing workflows.

The benefits of using this workflows include:

- There is a lack of data transfer and duplication because the S3 objects remain where they are.
- The folder-like structure in S3 is reproduced in Synapse to maintain the file organization.

Briefly, `nf-synindex` achieves this automation as follows:

1. Update the `owner.txt` file with the authenticated user ID
2. Register the Tower bucket as an external storage location
3. Mirror the directory-like structure in S3 as folders on Synapse
4. For each S3 object, the following steps are performed in parallel:
   1. Compute the MD5 checksum
   2. Register the S3 object as a file handle
   3. Expose the file handle as a Synapse file under the corresponding Synapse folder
5. Output a mapping between the S3 objects and the newly created Synapse files

**N.B.** The workflow assumes that the S3 bucket is [configured](https://help.synapse.org/docs/Custom-Storage-Locations.2048327803.html) for Synapse.

## Quickstart

The examples below demonstrate how you would index objects under an S3 prefix in a bucket called `example-bucket`.

1. Identify an S3 prefix that contains a set of objects that you want to index in Synapse (_e.g._ output files from a data processing workflow).

    **Example:** Objects under `s3://example-bucket/outputs/`

    ```text
    s3://example-bucket/outputs/foobar_1.trimming_report.txt
    s3://example-bucket/outputs/foobar_2.trimming_report.txt
    s3://example-bucket/outputs/fastqc/
    s3://example-bucket/outputs/fastqc/foobar_1_val_1_fastqc.html
    s3://example-bucket/outputs/fastqc/foobar_1_val_1_fastqc.zip
    s3://example-bucket/outputs/fastqc/foobar_2_val_2_fastqc.html
    s3://example-bucket/outputs/fastqc/foobar_2_val_2_fastqc.zip
    ```

2. Prepare your Synapse configuration file to authenticate the workflow. For more details, check out the [Authentication](#authentication) section.

    **Example:** Uploaded to `s3://example-bucket/synapse_config.ini`

    ```ini
    [authentication]
    authtoken = <personal-access-token>
    ```

3. Create a parent Synapse folder that will contain the indexed files and the associated folder structure.

    **Example:** Created a folder (`syn26601236`) under some project

    ```text
    synapse create --parentid <project-id> --name <folder-name> Folder
    ```

4. Prepare your parameters file. For more details, check out the [Parameters](#parameters) section.

    **Example:** Stored locally as `./params.yml`

    ```yaml
    s3_prefix: s3://example-bucket/outputs/
    synapse_config: s3://example-bucket/synapse_config.ini
    parent_id: syn26601236
    ```

5. Launch workflow using the [Nextflow CLI](https://nextflow.io/docs/latest/cli.html#run), the [Tower CLI](https://help.tower.nf/latest/cli/), or the [Tower web UI](https://help.tower.nf/latest/launch/launchpad/).

    **Example:** Launched using the Tower CLI

    ```console
    tw launch sage-bionetworks-workflows/nf-synindex --params-file=./params.yml
    ```

6. Explore the parent folder on Synapse.

    **Example:** Synapse files and folders under `syn26601236`

    ```text
    syn26601270  foobar_1.trimming_report.txt
    syn26601272  foobar_2.trimming_report.txt
    syn26601252  fastqc/
    syn26601268    foobar_1_val_1_fastqc.html
    syn26601267    foobar_1_val_1_fastqc.zip
    syn26601271    foobar_2_val_2_fastqc.html
    syn26601269    foobar_2_val_2_fastqc.zip
    ```

7. Explore the output file mapping the S3 objects and the corresponding Synapse file IDs.

    **Example:** Downloaded from `s3://example-bucket/outputs/synindex/under-syn26601236/file_ids.csv`

    ```text
    s3://example-bucket/outputs/foobar_1.trimming_report.txt,syn26601270
    s3://example-bucket/outputs/foobar_2.trimming_report.txt,syn26601272
    s3://example-bucket/outputs/fastqc/foobar_1_val_1_fastqc.html,syn26601268
    s3://example-bucket/outputs/fastqc/foobar_1_val_1_fastqc.zip,syn26601267
    s3://example-bucket/outputs/fastqc/foobar_2_val_2_fastqc.html,syn26601271
    s3://example-bucket/outputs/fastqc/foobar_2_val_2_fastqc.zip,syn26601269
    ```

## Authentication

Indexing files from Synapse requires the workflow to be authenticated. The workflow currently supports two authentication methods:

- **(Preferred)** Create a secret called `SYNAPSE_AUTH_TOKEN` containing a Synapse personal access token using the [Nextflow CLI](https://nextflow.io/docs/latest/secrets.html) or [Nextflow Tower](https://help.tower.nf/latest/secrets/overview/).
- Provide a Synapse configuration file containing a personal access token (see example above) to the `synapse_config` parameter. This method is best used if Nextflow/Tower secrets aren't supported on your platform. **Important:** Make sure that your `synapse_config` file is not stored in a directory that will be indexed on or uploaded to Synapse.

You can generate a personal access token using [this dashboard](https://www.synapse.org/#!PersonalAccessTokens:).

## Parameters

Check out the [Quickstart](#quickstart) section for example parameter values.

- **`s3_prefix`**: An S3 prefix containing a set of files that need to be indexed in Synapse. Typically, this corresponds to the value given to the `outdir` parameter from an nf-core workflow run.

- **`parent_id`**: The Synapse ID of a Synapse folder that will contain the indexed files and the associated folder structure.

- **`synapse_config`**: (Optional) A [Synapse configuration file](https://python-docs.synapse.org/build/html/Credentials.html#use-synapseconfig) containing authentication credentials. A minimal example is included in the [Quickstart](#quickstart) section.

## Known Limitations

- The workflow doesn't annotate the Synapse files it creates with any metadata or provenance.
- The workflow will index all of the objects under the given S3 prefix. There is no way to filter or skip the indexing of certain objects.
