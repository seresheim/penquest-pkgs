from typing import List

class OS:
    LINUX = 1
    WINDOWS = 2
    IOS = 3
    ANDROID = 4

    @staticmethod
    def get_all_oses() -> List["OS"]:
        return [OS.LINUX, OS.WINDOWS, OS.IOS, OS.ANDROID]