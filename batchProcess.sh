find $1 -maxdepth 1 -iname "*.csv" | while read fname
do
	echo $fname
	bname=$(basename "$fname")
	bname_no_ext="${bname%.*}"
	./rainfall_moving_window.py --infile "$fname" --outfile "hourly_reprocessed_Andy/$bname" --outplot "hourly_reprocessed_Andy/$bname_no_ext.pdf" --logger hobo --window 60
done
