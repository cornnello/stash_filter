#!/bin/bash

# create filter for grep
FILT_FILE=$1
STASH_FILE="updated_list.txt"
SRC_PATH=$2
DEST_PATH=$3

[[ $FILT_FILE = "NO" || $FILT_FILE = "no" ]] || [[ -r $FILT_FILE ]] || exit 1

if [ $FILT_FILE != "NO" -a $FILT_FILE != "no" ]; then
	$(dirname $0)/dist/stash_filter $SRC_PATH $STASH_FILE

	FILT_EXPR=""
	# concatenate filters and remove comments 
	for ID in $(sed 's/\s*#.*$//' $FILT_FILE | grep -v '^\s*$'); do
		FILT_EXPR+="${ID}\|"
	done
	FILT_EXPR=$(echo $FILT_EXPR | sed 's/^\(.\+\)\\|$/\1/') # remove last pipe

	grep "$FILT_EXPR" $STASH_FILE > downloads.txt

	# rclone copy "$SRC_PATH" "$DEST_PATH" -P --drive-server-side-across-configs --drive-stop-on-upload-limit --checksum --checkers=12 --fast-list --files-from downloads.txt
	rclone copy "$SRC_PATH" "$DEST_PATH" -P --drive-server-side-across-configs --drive-stop-on-upload-limit --fast-list --files-from downloads.txt

else
	$(dirname $0)/dist/stash_filter $SRC_PATH $STASH_FILE
	rclone copy "$SRC_PATH" "$DEST_PATH" -P --drive-server-side-across-configs --delete-excluded --drive-stop-on-upload-limit --checksum --fast-list --files-from $STASH_FILE
fi
