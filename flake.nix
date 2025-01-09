{
  description = "A Nix-flake development environment for robotic-arm ";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
    ...
  }: let
    # system should match the system you are running on
    system = "x86_64-linux";
  in {
    devShells."${system}".default = let
      pkgs = import nixpkgs {
        inherit system;
      };
    in
      pkgs.mkShell {
        packages = with pkgs; [
          python3
          python3Packages.bleak
          python3Packages.tkinter
          ruff
          mpremote
          rshell
        ];

        shellHook = ''
        '';
      };
  };
}
