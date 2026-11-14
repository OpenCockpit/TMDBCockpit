#!/bin/sh
echo src/gz cockpit-all https://opencockpit.github.io/Cockpit-Feed/packages/all > /etc/opkg/cockpit-feed-all.conf
echo src/gz cockpit-armv7ahf-neon https://opencockpit.github.io/Cockpit-Feed/packages/armv7ahf-neon > /etc/opkg/cockpit-feed-armv7ahf-neon.conf
