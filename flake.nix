{
  description = "podreader — podcast subscription and transcript management for AI agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
      in {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "podreader";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";

          build-system = [ python.pkgs.hatchling ];

          dependencies = with python.pkgs; [
            feedparser
            requests
            beautifulsoup4
            tomli-w
          ];

          # whisper-timestamped is optional — heavy ML dependency
          # Install separately or use whisper-cpp

          nativeCheckInputs = [ python.pkgs.pytest ];
          checkPhase = ''
            pytest tests/ -k "not test_transcripts"
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pkgs.uv
            pkgs.ffmpeg
          ];
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
        };
      });
}
