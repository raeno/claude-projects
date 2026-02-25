{ pkgs, ... }:

{
  # ---------------------------------------------------------------------------
  # Boot
  # ---------------------------------------------------------------------------
  boot.loader.grub = {
    enable = true;
    device = "/dev/sda";
  };

  # ---------------------------------------------------------------------------
  # Filesystems  (UUIDs confirmed from lsblk on the live Ubuntu system)
  # ---------------------------------------------------------------------------
  fileSystems."/" = {
    device = "/dev/disk/by-uuid/455fdbac-9e52-44af-9c9f-c6b644c5bcb5";
    fsType = "ext4";
  };

  fileSystems."/boot" = {
    device = "/dev/disk/by-uuid/66ef430a-e573-44d1-8451-659c024d893f";
    fsType = "ext3";
  };

  swapDevices = [
    { device = "/dev/disk/by-uuid/d281cb57-c618-456f-b728-4da37891ac2b"; }
  ];

  # ---------------------------------------------------------------------------
  # Networking  (Hetzner static /32 layout via systemd-networkd)
  # ---------------------------------------------------------------------------
  networking = {
    hostName = "my-server";
    useNetworkd = true;
    useDHCP = false;
  };

  systemd.network = {
    enable = true;

    networks."10-uplink" = {
      matchConfig.Name = "enp0s31f6";

      address = [
        "95.216.27.23/32"
        "2a01:4f9:2a:1b71::2/64"
      ];

      routes = [
        # IPv4 — /32 requires GatewayOnLink so the kernel accepts the off-subnet gateway
        {
          Gateway = "95.216.27.1";
          GatewayOnLink = true;
        }
        # IPv6
        {
          Gateway = "fe80::1";
        }
      ];

      dns = [ "185.12.64.1" "185.12.64.2" ];
    };
  };

  # ---------------------------------------------------------------------------
  # SSH
  # ---------------------------------------------------------------------------
  services.openssh = {
    enable = true;
    settings = {
      PasswordAuthentication = false;
      PermitRootLogin = "no";
    };
  };

  # ---------------------------------------------------------------------------
  # Docker
  # ---------------------------------------------------------------------------
  virtualisation.docker = {
    enable = true;
    enableOnBoot = true;
    autoPrune.enable = true;
  };

  # ---------------------------------------------------------------------------
  # PostgreSQL 17
  # NOTE: NixOS will initialise a fresh cluster on first boot.
  #       Back up existing data with `pg_dumpall` before reinstalling.
  # ---------------------------------------------------------------------------
  services.postgresql = {
    enable = true;
    package = pkgs.postgresql_17;
  };

  # ---------------------------------------------------------------------------
  # User raeno
  # ---------------------------------------------------------------------------
  users.users.raeno = {
    isNormalUser = true;
    uid = 1000;
    shell = pkgs.zsh;
    extraGroups = [ "wheel" "docker" ];
    openssh.authorizedKeys.keys = [
      "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9ORVBUMLCP/qqN79mnQ6QZoL2/AY15S5kk4cyrKEq6E5c1WpE29LdOZNHtRa66hbL/H6ymzzflPVGiRwzSrVOXoa+li5j3LA/tHDQcEP3Rnfa4om6YpGz4zT2wSetn7d9ChWN8jtHcUUkOEAztpfAoMhuanMcRLBPOPs0L1VAi6RO3utT41MRKLJUDtsg6voy0X1uOtzG77o3w4vkfjmZ5PJWU7kmg+lwg0944WQavP6J1FbC2WpUG3jPB8zTosxDELLWWoiR9AM8qT1eVMjhABcA0ChGp/AizAvpRtOv+QFdB8XxxsAxA+hs4jYAwkVU9nux3lL7kDbHxKp/1PuH just.raeno@gmail.com"
    ];
  };

  programs.zsh.enable = true;

  security.sudo.wheelNeedsPassword = false;

  # ---------------------------------------------------------------------------
  # System packages
  # ---------------------------------------------------------------------------
  environment.systemPackages = with pkgs; [
    htop
    curl
    wget
    git
    ripgrep
    jq
    neovim
    tmux
    go
    mtr
    tcpdump
    strace
    openssh
    zsh
    claude-code
  ];

  # ---------------------------------------------------------------------------
  # Locale / timezone
  # ---------------------------------------------------------------------------
  time.timeZone = "UTC";
  i18n.defaultLocale = "en_US.UTF-8";

  system.stateVersion = "25.05";
}
