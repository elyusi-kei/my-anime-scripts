import argparse
import os
from pathlib import Path
import random
import re
from ripgrepy import Ripgrepy
import subprocess

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import RadioList, Label
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.formatted_text import HTML


# https://discuss.python.org/t/correct-way-to-remove-all-file-extensions-from-a-path-with-pathlib/6711/2
def strip_subtitle_extensions(path: Path):
    while path.suffix in {".srt", ".ass", ".ja"}:
        path = path.with_suffix("")
    return path


# https://github.com/prompt-toolkit/python-prompt-toolkit/issues/756
def radiolist_prompt(
    title: str = "",
    values=None,
    default=None,
    cancel_value=None,
    style=None,
    async_: bool = False,
):
    # Create the radio list
    radio_list = RadioList(values, default)
    # Remove keybinds to rebind later
    radio_list.control.key_bindings.remove("enter")
    radio_list.control.key_bindings.remove(" ")
    # make the radio buttons take up less space, i.e. (*)->*
    radio_list.open_character = ""
    radio_list.close_character = ""

    bindings = KeyBindings()

    @bindings.add("enter")
    @bindings.add(" ")
    @bindings.add(Keys.WindowsMouseEvent)
    def exit_with_value(event):
        """
        Enter/Space/Clicking sets the entry as selected and launches mpv
        """
        event_data = event.data.split(";")

        # eg: ['LEFT', 'MOUSE_DOWN', '42', '28']
        if len(event_data) >= 4 and event_data[1] == "MOUSE_UP":
            result_index = int(event_data[3]) - 1  # skip title line
            if result_index >= len(values):  # ignore outside of bounds clicks
                return
            # https://github.com/prompt-toolkit/python-prompt-toolkit/blob/5b3dd6dbbd72ac8323e749cc12e6aa2d7c7411af/src/prompt_toolkit/widgets/base.py#L796
            radio_list._selected_index = result_index
            radio_list._handle_enter()
            open_video_for_result(radio_list.current_value)
            return
        elif event_data[0] in ["\r", " "]:
            # as in on entering being selected, not key enter
            radio_list._handle_enter()
            open_video_for_result(radio_list.current_value)
            return
            # event.app.exit(result=radio_list.current_value)
        # else:
        #     event.app.exit(result=event_data)

    @bindings.add("q")
    @bindings.add("c-c")
    def backup_exit_with_value(event):
        """
        Pressing Q or Ctrl-C will exit the user interface with the cancel_value.
        """
        event.app.exit(result=cancel_value)

    # Create and run the mini inline application
    application = Application(
        layout=Layout(HSplit([Label(title), radio_list])),
        key_bindings=merge_key_bindings([load_key_bindings(), bindings]),
        mouse_support=True,
        style=style,
        full_screen=True,
    )
    if async_:
        return application.run_async()
    else:
        return application.run()


def open_video_for_result(rg_result):
    subtitle_path = Path(rg_result["data"]["path"]["text"])
    line_num = rg_result["data"]["line_number"] - 1

    if subtitle_path.suffix == ".srt":
        with open(subtitle_path, "r", encoding="utf-8") as subs:
            sub_lines = [line.rstrip() for line in subs]
        current_line_num = line_num - 1
        regex = re.compile(r"^\s*(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)")
        while current_line_num >= 0:
            if match := regex.match(sub_lines[current_line_num]):
                timestamp = match.group(1).replace(",", ".")
                break
            current_line_num -= 1
        else:
            print(f"Couldn't find a valid timestamp for before line {line_num}")
            return
    elif subtitle_path.suffix == ".ass":
        print("TODO")
        return
    else:
        print("unknown sub filetype")
        return

    fname = strip_subtitle_extensions(subtitle_path)

    valid_video_extensions = [".mp4", ".mkv"]
    for ext in valid_video_extensions:
        vid = fname.parents[1] / (fname.name + ext)
        if vid.exists():
            break
    else:
        print(f"couldn't find video for subtitle {subtitle_path}")

    command = ["mpv", f"--start={timestamp}", str(vid)]
    subprocess.Popen(command, start_new_session=True)


def main(args):
    anime_dir = Path(args.dir)
    rg = Ripgrepy(args.search_string, anime_dir).g("**/subs/*.srt").g("**/subs/*.ass")
    results = rg.line_number().json().run().as_dict

    # since we can have more results than a 1 screen can show, limit results to 1 screen height's worth
    result_count_limit = os.get_terminal_size().lines - 1
    # since results can be omitted, randomly pick each time for some extra gamba 🎲🎲
    omitted_num = max(0, len(results) - result_count_limit)
    results = random.sample(results, k=min(result_count_limit, len(results)))
    prompt_choices = []

    regex = re.compile(args.search_string)
    for result in results:
        line = result["data"]["lines"]["text"].strip()
        line = regex.sub(lambda m: f'<style fg="#E6B673">{m.group(0)}</style>', line)
        extless_path = strip_subtitle_extensions(Path(result["data"]["path"]["text"]))
        prompt_choices.append(
            (
                result,
                HTML(
                    f"{line} "
                    f'<style fg="#444">{extless_path.parents[1].stem}/{extless_path.stem}</style>'
                ),
            )
        )

    _ = radiolist_prompt(
        title=f"検索結果（{omitted_num}件省略されました）：" if omitted_num > 0 else "検索結果：",
        values=prompt_choices,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("search_string")
    parser.add_argument(
        "-d",
        "--dir",
        help="path to root anime directory to search through",
        default=Path(__file__).parents[1],  # parent 0 is this directory
    )

    args = parser.parse_args()
    main(args)
