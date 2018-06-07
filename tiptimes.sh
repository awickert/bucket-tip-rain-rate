find $1 -maxdepth 1 -iname "*.csv" | while read fname
do
	echo $fname
	bname=$(basename "$fname")
	bname_no_ext="${bname%.*}"
	./rainfall_moving_window.py --infile "$fname" --tipfile "tiptimes/$bname" --logger hobo
done
