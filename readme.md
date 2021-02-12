tzcolors.io SmartContracts
====================================

Build/Basic Usage
-----------------

### Dependencies

This project depends only on SmartPy, you can install SmartPy by doing a:

```
$ sh <(curl -s https://smartpy.io/cli/install.sh)
```

You can read more about the installation here: https://smartpy.io/cli/

If you feel lazy you can simply copy/paste the entire 'auction_house.py' content into the web IDE: https://smartpy.io/ide 

### Build

```
$ /home/coder/smartpy-cli/SmartPy.sh compile auction_house.py "AuctionHouse()" out
$ /home/coder/smartpy-cli/SmartPy.sh compile auction_house.py "TZColorsFA2(sp.address('KT1CpeSQKdkhWi4pinYcseCFKmDhs5M74BkU'))" out
```

In our example above  KT1CpeSQKdkhWi4pinYcseCFKmDhs5M74BkU is the address of the deployed auction house.

### Test
```
$ /home/coder/smartpy-cli/SmartPy.sh test auction_house.py out
```