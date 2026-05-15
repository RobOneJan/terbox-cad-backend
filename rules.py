import math
from models import TerBoxConfiguration, ComputedConfig, SizeOption

_MODULE_LENGTH_CM = 125.0

_SIZE_MODULE_COUNT = {
    SizeOption.small: 1,
    SizeOption.medium: 2,
    SizeOption.large: 3,
}


def compute_config(config: TerBoxConfiguration) -> ComputedConfig:
    if config.customSize:
        try:
            total_length_cm = float(config.customSize.length)
        except (ValueError, TypeError):
            total_length_cm = _SIZE_MODULE_COUNT[config.size] * _MODULE_LENGTH_CM
        module_count = max(1, math.ceil(total_length_cm / _MODULE_LENGTH_CM))
        module_length_cm = round(total_length_cm / module_count, 2)
    else:
        module_count = _SIZE_MODULE_COUNT[config.size]
        module_length_cm = _MODULE_LENGTH_CM
    return ComputedConfig(module_count=module_count, module_length_cm=module_length_cm)
