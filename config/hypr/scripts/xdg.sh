#!/bin/bash

_sleep1="0.1"
_sleep2="0.5"
_sleep3="2"
_sleep4="1"

sleep $_sleep2

killall -e xdg-desktop-portal-hyprland
killall -e xdg-desktop-portal-gtk
killall -e xdg-desktop-portal

dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP=hyprland
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP

systemctl --user stop pipewire
systemctl --user stop wireplumber
systemctl --user stop xdg-desktop-portal
systemctl --user stop xdg-desktop-portal-gtk
systemctl --user stop xdg-desktop-portal-hyprland
sleep $_sleep1

systemctl --user start pipewire
systemctl --user start wireplumber
systemctl --user start xdg-desktop-portal
systemctl --user start xdg-desktop-portal-gtk
systemctl --user start xdg-desktop-portal-hyprland

sleep $_sleep4
