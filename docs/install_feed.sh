#!/bin/sh
echo src/gz cockpit-all https://opencockpit.github.io/Cockpit-Feed/packages/all > /etc/opkg/cockpit-feed-all.conf
echo src/gz cockpit-armhf https://opencockpit.github.io/Cockpit-Feed/packages/armhf > /etc/opkg/cockpit-feed-armhf.conf
