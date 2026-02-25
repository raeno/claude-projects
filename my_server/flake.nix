{
  description = "my_server - declarative package management with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    lib = nixpkgs.lib;
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      config.allowUnfreePredicate = pkg:
        builtins.elem (lib.getName pkg) [
          "claude-code"
        ];
    };
  in {
    # Run `nix develop` to enter a shell with all server packages available
    devShells.${system}.default = pkgs.mkShell {
      name = "my_server";

      packages = with pkgs; [
        # System utilities
        htop
        curl
        wget
        git
        ripgrep
        jq
        openssh

        # Claude Code CLI
        claude-code

        # Amnezia VPN
        amnezia-vpn

        # PostgreSQL 17
        postgresql_17

        # Add more packages below as needed
        # e.g. nginx, postgresql, nodejs, python3, etc.
      ];

      shellHook = ''
        echo "my_server environment loaded"
        echo "Available packages: $(echo $buildInputs | tr ' ' '\n' | grep -o '[^-]*$' | sort | tr '\n' ' ')"

        if [ -z "$SSH_AUTH_SOCK" ]; then
          eval $(ssh-agent -s)
          echo "ssh-agent started (pid $SSH_AGENT_PID)"
        else
          echo "ssh-agent already running"
        fi
      '';
    };

    # Run `nix build` to build a package collection
    packages.${system}.default = pkgs.buildEnv {
      name = "my_server-packages";
      paths = with pkgs; [
        htop
        curl
        wget
        git
        ripgrep
        jq
        openssh
        claude-code
        amnezia-vpn
        postgresql_17
      ];
    };
  };
}
