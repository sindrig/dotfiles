#!/usr/bin/env bash
set -e
sudo pacman -S git
(
	git clone https://aur.archlinux.org/yay.git
	cd yay
	makepkg -si
	cd ..
	rm -r yay
)

curl -O https://download.sublimetext.com/sublimehq-pub.gpg && sudo pacman-key --add sublimehq-pub.gpg && sudo pacman-key --lsign-key 8A8F901A && rm sublimehq-pub.gpg
echo -e "\n[sublime-text]\nServer = https://download.sublimetext.com/arch/dev/x86_64" | sudo tee -a /etc/pacman.conf
yay -Sy
yay -S - < pkglist.txt

sudo gpasswd -a sindri bumblebee
sudo systemctl enable bumblebeed

mkdir ~/.cache/spotifyd