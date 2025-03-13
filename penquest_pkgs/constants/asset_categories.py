from typing import List

class AssetCategory:
    MOBILE = 1
    CLOUD = 2
    DMZ = 3
    LAN = 4
    WEB_SERVER = 5
    MAIL_SERVER = 6
    APP_SERVER = 7
    FILE_SERVER = 8
    DATABASE = 9
    CLIENT = 10
    NETWORK_APPLIANCE = 11
    IOT = 12
    CONTAINER = 13
    INDUSTRIAL_SYSTEM = 14
    SCADA = 15
    DEVICE = 16

    @staticmethod
    def get_all_categories() -> List["AssetCategory"]:
        return [
            AssetCategory.MOBILE,
            AssetCategory.CLOUD,
            AssetCategory.DMZ,
            AssetCategory.LAN,
            AssetCategory.WEB_SERVER,
            AssetCategory.MAIL_SERVER,
            AssetCategory.APP_SERVER,
            AssetCategory.FILE_SERVER,
            AssetCategory.DATABASE,
            AssetCategory.CLIENT,
            AssetCategory.NETWORK_APPLIANCE,
            AssetCategory.IOT,
            AssetCategory.CONTAINER,
            AssetCategory.INDUSTRIAL_SYSTEM,
            AssetCategory.SCADA,
            AssetCategory.DEVICE,
        ]