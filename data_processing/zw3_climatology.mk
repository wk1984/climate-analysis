# zw3_climatology.mk
#
# To execute:
#   make -n -f zw3_climatology.mk  (-n is a dry run)
#   (must be run from the directory that the relevant matlab scripts are in)

# Fix:
#   At the moment the data processing (e.g. for the sf and calculation of the
#   running mean) doesn't do all the way back to the original files.


### Define marcos ###

include zw3_climatology_config.mk


### Core zonal wave 3 climatology process ###

## Phony target
all : ${RWID_DIR}/figures/env-${WAVE_LABEL}-va_Merra_250hPa_${TSCALE}_${GRID}_${PLOT_END}.png

## Step 1: Regrid the meridional wind data
${PDATA_DIR}/va_Merra_250hPa_${TSCALE}_${GRID}.nc : ${DATA_DIR}/va_Merra_250hPa_${TSCALE}_native.nc
	cdo remapcon2,${GRID} $< $@
	ncatted -O -a axis,time,c,c,T $@

## Step 2: Extract the wave envelope
${RWID_DIR}/env-${WAVE_LABEL}-va_Merra_250hPa_${TSCALE}_${GRID}.nc : ${PDATA_DIR}/va_Merra_250hPa_${TSCALE}_${GRID}.nc
	${ENV_METHOD} $< va $@ ${WAVE_SEARCH}

## Step 3: Calculate the hovmoller diagram
${RWID_DIR}/env-${WAVE_LABEL}-va_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}.nc : ${RWID_DIR}/env-${WAVE_LABEL}-va_Merra_250hPa_${TSCALE}_${GRID}.nc
	cdo ${MER_METHOD} -sellonlatbox,0,360,${LAT_SEARCH_MIN},${LAT_SEARCH_MAX} $< $@
	ncatted -O -a axis,time,c,c,T $@

## Step 4: Calculate the wave statistics
${RWID_DIR}/zw3-stats_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}.csv : ${RWID_DIR}/env-${WAVE_LABEL}-va_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}.nc
	${CDAT} ${DATA_SCRIPT_DIR}/calc_wave_stats.py $< env ${AMP_MIN} $@ 

## Step 5: Generate list of dates for use in composite creation
${RWID_DIR}/zw3-dates_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}-extentmin${EXTENT_MIN}.txt : ${RWID_DIR}/zw3-stats_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}.csv
	${PYTHON} ${DATA_SCRIPT_DIR}/parse_wave_stats.py $< --extent_filter ${EXTENT_MIN} --date_list $@

## Step 5a: Plot the extent histogram
${RWID_DIR}/figures/zw3-extent-histogram_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}-extentmin${EXTENT_MIN}.png : ${RWID_DIR}/zw3-stats_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}.csv
	${PYTHON} ${DATA_SCRIPT_DIR}/parse_wave_stats.py $< --extent_filter ${EXTENT_MIN} --extent_histogram $@

## Step 5b: Plot the monthly totals histogram
${RWID_DIR}/figures/zw3-monthly-totals-histogram_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}-extentmin${EXTENT_MIN}.png : ${RWID_DIR}/zw3-stats_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}.csv
	${PYTHON} ${DATA_SCRIPT_DIR}/parse_wave_stats.py $< --extent_filter ${EXTENT_MIN} --monthly_totals_histogram $@

## Step 5c: Plot the monthly totals histogram
${RWID_DIR}/figures/zw3-seasonal-values-histogram_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}-extentmin${EXTENT_MIN}.png : ${RWID_DIR}/zw3-stats_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}.csv
	${PYTHON} ${DATA_SCRIPT_DIR}/parse_wave_stats.py $< --extent_filter ${EXTENT_MIN} --seasonal_values_histogram $@ --annual

## Step 6: Plot the envelope
${RWID_DIR}/figures/env-${WAVE_LABEL}-va_Merra_250hPa_${TSCALE}_${GRID}_${PLOT_END}.png : ${RWID_DIR}/env-${WAVE_LABEL}-va_Merra_250hPa_${TSCALE}_${GRID}.nc ${RWID_DIR}/zw3-stats_Merra_250hPa_${TSCALE}_${GRID}-${MER_METHOD}-${LAT_LABEL}_env-${WAVE_LABEL}-va-ampmin${AMP_MIN}.csv ${PDATA_DIR}/sf_Merra_250hPa_${TSCALE}-zonal-anom_native.nc
	${CDAT} ${VIS_SCRIPT_DIR}/plot_envelope.py $< env daily --extent $(word 2,$^) ${LAT_SEARCH_MIN} ${LAT_SEARCH_MAX} --contour $(word 3,$^) sf --time ${PLOT_START} ${PLOT_END} none --projection spstere --ofile $@

## Step 6a: Calculate the streamfunction zonal anomaly
${PDATA_DIR}/sf_Merra_250hPa_${TSCALE}-zonal-anom_native.nc : ${PDATA_DIR}/sf_Merra_250hPa_${TSCALE}_native.nc       
	${ZONAL_ANOM_METHOD} $< sf $@
	ncatted -O -a axis,time,c,c,T $@




## Optional extras ##

# plot_composite.py   --   plot a composite
