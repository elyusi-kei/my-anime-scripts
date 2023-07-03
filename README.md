Just some small JP subtitle-related scripts I wanted but couldn't find. Probably less because they didn't exist and more I'm just bad at finding them.  
Some of the design choices are probably strange, but I wasn't planning to share until 栗 asked. I only use them on Windows, so fix PRs for superior OSes welcome. Likewise for file extensions I haven't bothered with yet.

Expected installations:

- `python` 3.10
- `mpv` as the video player
- `ffprobe` as part of an `ffmpeg` installation for `retime.py`
- `rg` ([`ripgrep`](https://github.com/BurntSushi/ripgrep)) for `search.py`
- `pip install -r requirements.txt` or the like

## retime.py

A script for batch retiming a season of episodes with manually specified offsets. 

Currently only a main offset and an optional offset for the second half of each episode is available. The episode midpoint information is based on extracted chapter info. If your totally legal copies of episodes lack them, ¯\\\_(ツ)_/¯.


An example of expected directory structure is:

    機動戦士ガンダム00 S1/
    ├─ subs_orig/
    │  ├─ retime.toml
    │  ├─ sub001.srt
    │  ├─ sub002.srt
    │  ├─ ...
    ├─ S01 E01.mkv
    ├─ S01 E02.mkv
    ├─ ...

where the script is expected to be run in root of this structure (at the episodes level), or passed the directory as an argument. If no `retime.toml` exists, it will be made, and then the script can be re-run after editing. The other file names are not important, and subtitles will be matched to episodes both alphabetically.

The expected structure on completion is:

<pre><code>機動戦士ガンダム00 S1/
├─ subs_orig/
│  ├─ retime.toml
│  ├─ sub001.srt
│  ├─ sub002.srt
│  ├─ ...
<strong>├─ subs/
│  ├─ S01 E01.ja.srt
│  ├─ S01 E02.ja.srt
│  ├─ ...</strong>
├─ S01 E01.mkv
├─ S01 E02.mkv
├─ ...
</pre></code>

For mpv to find the subtitles in ``subs/``, something like

    sub-file-paths=subs

needs to be added to ``mpv.conf``.

<details>
<summary>Why I wanted this</summary>

I wanted to retime some JP subs for a show, and messing around a bit it was clear there was one offset for the first half of the show and a ~1sec different offset for the second half after the midpoint break.   
I tried to get `ALASS`/`FFsubsync` to automagically retime them, but without splits they just settled on a timing in the middle that wasn't very satisfactory. And with `ALASS` allowed any amount of splits, it got really confused instead of splitting where I wanted.

So now I'm splitting where I want with this script; currently I've only needed to split first and second half. If I run into a trickier case - probably a movie - I'll extend things then. PRs welcome too.

The below above example uses Gundam 00 because that's what I was trying to retime.

I chose this directory structure because I dislike having subtitle files clutter the view of my video files, and this seemed like a reasonable approach. I keep the original subtitles separate for easier redos (edit the file and rerun the script).
</details>

## search.py

A script that recursively searches for JP subtitles in a structure like those created by `retime.py` for a supplied search target. Clicking any of the results opens `mpv` at the point where the subtitle happens.

Q/Ctrl+C to quit.

By default, the root directory searched is one level up from this script's directory. A different directory can be specified with `--dir`.

<details>
<summary>Why</summary>

I wanted something a tiny bit like [Immersion Kit](https://www.immersionkit.com/) for searching through my local subtitles for vocab.

As for the choice of default directory: having my scripts folder live inside my anime folder just seemed like less fuss than setting up some kind of config.
</details>

## Misc

<details>
<summary>Aliases</summary>

As a reminder, don't forget to alias judiciously. On Windows I have this in `profile.ps1` for `pwsh`:


<pre language="powershell"><code language="powershell">function ..retime { python "<b>&lt;SNIP&gt;</b>/retime.py" @args }
function ..search { python "<b>&lt;SNIP&gt;</b>/search.py" @args }
</pre></code>

`..` as a prefix in function names is legal and doesn't conflict with anything AFAIK, which allows for really generic naming. `,retime` and the like being valid *nix scripts is the  [inspiration](https://rhodesmill.org/brandon/2009/commands-with-comma/) here.
</details>

Feel free to message me:  
![](https://dcbadge.vercel.app/api/shield/170925540855775242?style=flat)


<style type="text/css">
strong {color:#FF8F40;}
b {color:#ACB6BF8C}
</style>
