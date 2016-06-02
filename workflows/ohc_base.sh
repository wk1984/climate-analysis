#
# Description: Script for running the ohc_base.mk workflow for a given model/experiment combo
#

function usage {
    echo "USAGE: bash $0 model experiments"
    echo "   e.g. bash $0 CSIRO-Mk3-6-0 historical noAA"
    exit 1
}

# Read inputs

OPTIND=1 
options=' '
while getopts ":nB" opt; do
  case $opt in
    n)
      options+=' -n' >&2
      ;;
    B)
      options+=' -B' >&2
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done
shift $((OPTIND-1))

model=$1
shift
experiments=( $@ )

# Determine runs based on model and experiment

volrun='r0i0p0'
for experiment in "${experiments[@]}"; do
    if [[ ${model} == 'CSIRO-Mk3-6-0' && ${experiment} == 'historical' ]] ; then
        runs=(  r2i1p1 r3i1p1 ) 
        #r1i1p1 r4i1p1 r5i1p1 r6i1p1 r7i1p1 r8i1p1 r9i1p1 r10i1p1
        organisation='CSIRO-QCCCE'

    elif [[ ${model} == 'CSIRO-Mk3-6-0' && ${experiment} == 'historicalGHG' ]] ; then
        runs=( r1i1p1 r2i1p1 r3i1p1 ) 
        #r4i1p1 r5i1p1 r6i1p1 r7i1p1 r8i1p1 r9i1p1 r10i1p1
        organisation='CSIRO-QCCCE'

    elif [[ ${model} == 'CSIRO-Mk3-6-0' && ${experiment} == 'historicalNat' ]] ; then
        runs=( r1i1p1 r2i1p1 r3i1p1 ) 
        #r4i1p1 r5i1p1 r6i1p1 r7i1p1 r8i1p1 r9i1p1 r10i1p1
        organisation='CSIRO-QCCCE'

    elif [[ ${model} == 'CSIRO-Mk3-6-0' && ${experiment} == 'noAA' ]] ; then
        experiment='historicalMisc'
        runs=( r1i1p3 r2i1p3 r3i1p3 )
        #r4i1p3 r5i1p3 r6i1p3 r7i1p3 r8i1p3 r9i1p3 r10i1p3
        organisation='CSIRO-QCCCE'
        volrun='r0i0p3'

    elif [[ ${model} == 'CSIRO-Mk3-6-0' && ${experiment} == 'AA' ]] ; then
        experiment='historicalMisc'
        runs=( r1i1p4 r2i1p4 r3i1p4 )
        #r4i1p4 r5i1p4 r6i1p4 r7i1p4 r8i1p4 r9i1p4 r10i1p4
        organisation='CSIRO-QCCCE'
        volrun='r0i0p4'

    elif [[ ${model} == 'ACCESS1-0' && ${experiment} == 'historical' ]] ; then
        runs=( r1i1p1 ) # incomplete
        organisation='CSIRO-BOM'

    else
        echo "Unrecognised model (${model}) / experiment (${experiment}) combination"
        usage
    fi

    for run in "${runs[@]}"; do
        sed -i "s/^\(ORGANISATION\s*=\s*\).*$/\ORGANISATION=${organisation}/" ohc_config.mk
        sed -i "s/^\(MODEL\s*=\s*\).*$/\MODEL=${model}/" ohc_config.mk
        sed -i "s/^\(EXPERIMENT\s*=\s*\).*$/EXPERIMENT=${experiment}/" ohc_config.mk
        sed -i "s/^\(RUN\s*=\s*\).*$/\RUN=${run}/" ohc_config.mk
        sed -i "s/^\(VOLUME_RUN\s*=\s*\).*$/\VOLUME_RUN=${volrun}/" ohc_config.mk
        make ${options} -f ohc_base.mk
        echo "DONE: ${model} ${experiment} ${run}: make ${options} -f ohc_base.mk"
    done
done






