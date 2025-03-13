class EquipmentType():
    ATTACK_TOOL = "AttackTool"
    MALWARE = "Malware"
    EXPLOIT = "Exploit"
    CREDENTIALS = "Credentials"
    SECURITY_SYSTEM = "SecuritySystem"
    FAILOVER = "Failover"
    FIX = "Fix"
    POLICY = "Policy"


ATTACK_EQUIPMENT_TYPES = [
    EquipmentType.ATTACK_TOOL,
    EquipmentType.MALWARE,
    EquipmentType.EXPLOIT,
    EquipmentType.CREDENTIALS,
]

DEFENSE_EQUIPMENT_TYPES = [
    EquipmentType.SECURITY_SYSTEM,
    EquipmentType.FAILOVER,
    EquipmentType.FIX,
    EquipmentType.POLICY,
]   

PERMANENT_EQUIPMENT_TYPES = [
    EquipmentType.ATTACK_TOOL,
    EquipmentType.SECURITY_SYSTEM,
    EquipmentType.POLICY,
]

LOCAL_EQUIPMENT_TYPES = [
    EquipmentType.MALWARE,
    EquipmentType.EXPLOIT,
    EquipmentType.CREDENTIALS,
    EquipmentType.FAILOVER,
    EquipmentType.FIX,
]