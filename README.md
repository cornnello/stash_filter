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