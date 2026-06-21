import cv2
import mss
import numpy as np

WINDOW = "ROI Tuner - prompt_monitor"
ZOOM = 4

TOP_MIN, TOP_MAX, TOP_INIT = 850, 980, 920
LEFT_MIN, LEFT_MAX, LEFT_INIT = 620, 720, 670
WIDTH_MIN, WIDTH_MAX, WIDTH_INIT = 15, 60, 37
HEIGHT_MIN, HEIGHT_MAX, HEIGHT_INIT = 15, 60, 36

_last_printed = None


def _trackbar_pos(name):
    return cv2.getTrackbarPos(name, WINDOW)


def get_prompt_monitor():
    return {
        "top": _trackbar_pos("Top") + TOP_MIN,
        "left": _trackbar_pos("Left") + LEFT_MIN,
        "width": _trackbar_pos("Width") + WIDTH_MIN,
        "height": _trackbar_pos("Height") + HEIGHT_MIN,
    }


def print_prompt_monitor():
    global _last_printed
    roi = get_prompt_monitor()
    line = (
        f'prompt_monitor = {{"top": {roi["top"]}, "left": {roi["left"]}, '
        f'"width": {roi["width"]}, "height": {roi["height"]}}}'
    )
    if line != _last_printed:
        print(line, flush=True)
        _last_printed = line


def on_trackbar_change(_):
    print_prompt_monitor()


def main():
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)

    cv2.createTrackbar("Top", WINDOW, TOP_INIT - TOP_MIN, TOP_MAX - TOP_MIN, on_trackbar_change)
    cv2.createTrackbar("Left", WINDOW, LEFT_INIT - LEFT_MIN, LEFT_MAX - LEFT_MIN, on_trackbar_change)
    cv2.createTrackbar("Width", WINDOW, WIDTH_INIT - WIDTH_MIN, WIDTH_MAX - WIDTH_MIN, on_trackbar_change)
    cv2.createTrackbar("Height", WINDOW, HEIGHT_INIT - HEIGHT_MIN, HEIGHT_MAX - HEIGHT_MIN, on_trackbar_change)

    print("Keo slider de tinh chinh ROI. Copy chuoi prompt_monitor tu Terminal.")
    print("Nhan Q tren cua so preview de thoat.\n")
    print_prompt_monitor()

    with mss.mss() as sct:
        while True:
            roi = get_prompt_monitor()
            scr = np.array(sct.grab(roi))
            img = cv2.cvtColor(scr, cv2.COLOR_BGRA2BGR)
            preview = cv2.resize(
                img,
                (roi["width"] * ZOOM, roi["height"] * ZOOM),
                interpolation=cv2.INTER_NEAREST,
            )
            cv2.imshow(WINDOW, preview)

            if cv2.waitKey(25) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
