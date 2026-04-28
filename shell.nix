{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.streamlit
    pkgs.python3Packages.pandas
    pkgs.python3Packages.google-api-python-client
    pkgs.python3Packages.google-auth-oauthlib
    pkgs.python3Packages.google-auth-httplib2
  ];

  shellHook = ''
    echo " 🐒 Sektor 1255: Pummeluff-Radar mit Cloud-Sync bereit! 🔥"
    echo " Starte das Dashboard mit: streamlit run Pummeluff.py"
  '';
}
