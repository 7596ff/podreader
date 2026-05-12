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

          # faster-whisper for transcription (CTranslate2 backend, ~4x faster than openai-whisper)
          propagatedBuildInputs = [ python.pkgs.faster-whisper ];

          nativeCheckInputs = [ python.pkgs.pytest ];
          checkPhase = ''
            pytest tests/ -k "not test_transcripts"
          '';

          makeWrapperArgs = [
            "--prefix" "PATH" ":" "${pkgs.ffmpeg}/bin"
          ];
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pkgs.uv
            pkgs.ffmpeg
          ];
        };
      });
}
