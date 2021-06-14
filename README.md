# Stash filter

You give it an rclone switch stash, it gives you only the latest versions of the titles (that easy). 

## Installation
Have python installed (prefferably 3.6+). Use your favourite termial to got the folder and install the script with 

```
pip install -e .
```

**Alternative**

You can also use the prepackaged executables from `dist`. On Windows you MUST run the script from the same folder as rclone!

## Usage
Sample usage:

```
stash_filter -p stash_remote: files.txt
```

This will generate a file files.txt which you can now use to filter your rclone commands:

```
rclone copy stash_remote: my_stash: --files-from files.txt
```

## Using the filter bash script

The filte bash script can take a filter file (format below) which can be used to selectively add titles to you stash clone. The most effective way to use this is to have a list of base contant ids (content ids without 4 last digits). The cloning script will copy all the latest versions of the files matching the filter list from SRC to DEST.

In the release archive, there is a sample filter file. Sample usage:

```
mkdir roms
./update_stash.sh filter.txt "stash_remote:NSZ" ./roms
```

Credits: `cornnello#3116`
