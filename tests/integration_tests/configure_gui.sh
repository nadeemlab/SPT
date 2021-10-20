#!/usr/bin/expect -f

set force_conservative 1  ;
if {$force_conservative} {
	set send_slow {1 .01}
	proc send {ignore arg} {
		sleep .05
		exp_send -s -- $arg
	}
}

set timeout -1
spawn spt-pipeline configure
match_max 100000
expect "\[33m\[0m\r
\[33m spt_version \[0m\[1;36m*\[0m\[33m\[0m\r
\[33m \[0m\[34mhttps://github.com/nadeemlab/SPT\[0m\[33m\[0m\r
\[33m\[0m\r
\[33mThis dialog solicits parameters for your SPT pipeline run and generates a JSON\[0m\r
\[33mconfiguration file.\[0m\r
\[33m\[0m\r
\[33mWorkflows:\[0m\r
\[33m \[0m\[36mMultiplexed IF density\[0m\[33m\[0m\r
\[33m \[0m\[36mMultiplexed IF diffusion\[0m\[33m\[0m\r
\[33m \[0m\[36mMultiplexed IF front proximity\[0m\[33m\[0m\r
\[33m \[0m\[36mMultiplexed IF phenotype proximity\[0m\[33m\[0m\r
\[33mEnter the computational workflow type:\[0m "
send -- "Multiplexed IF phenotype proximity\r"
expect -exact "Multiplexed IF phenotype proximity\r
\[33mEnter the Singularity container file (.sif) containing the toolbox:\[0m "
send -- "example.sif\r"
expect -exact "example.sif\r
\[33mEnter the path containing input CSV files pertaining to cells:\[0m "
send -- "data/\r"
expect -exact "data/\r
\[33mEnter the file manifest file:\[0m "
send -- "data/file_manifest.tsv\r"
expect -exact "data/file_manifest.tsv\r
\[33mEnter comma-separated list of compartment names:\[0m "
send -- "Tumor,Non-Tumor\r"
expect -exact "Tumor,Non-Tumor\r
\[33mBalanced/symmetric analysis with respect to phenotype pairs?\[0m "
send -- "No\r"
expect -exact "No\r
\[33mRuntime platforms:\[0m\r
\[33m \[0m\[36mlsf\[0m\[33m\[0m\r
\[33m \[0m\[36mlocal\[0m\[33m\[0m\r
\[33mSelect runtime platform:\[0m "
send -- "local\r"
expect -exact "local\r
\[33mSkip file integrity check?\[0m "
send -- "No\r"
expect eof
