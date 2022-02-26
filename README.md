# EnOcean integration for Home Assistant
Home Assistant integration of the EnOcean network. This integration sets the actual status of all switches in Home Assistant according to the telegrams sent back by each device.

## Installation

### Manual Installation
```
cd ./config/custom_components
git clone https://github.com/refohl/ha_my_enocean.git my_enocean
```

### HACS
Add the GitHub URL of this repository to the *Custom repositories* of HACS and select *Integration* as category.