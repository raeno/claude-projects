{
  description = "my_server - declarative package management with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
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

        # Claude Code CLI
        claude-code

        # Amnezia VPN
        amnezia-vpn

        # PostgreSQL 18
        postgresql18

        # Add more packages below as needed
        # e.g. nginx, postgresql, nodejs, python3, etc.
      ];

      shellHook = ''
        echo "my_server environment loaded"
        echo "Available packages: $(echo $buildInputs | tr ' ' '\n' | grep -o '[^-]*$' | sort | tr '\n' ' ')"
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
        claude-code
        amnezia-vpn
        postgresql18
      ];
    };
  };
}
