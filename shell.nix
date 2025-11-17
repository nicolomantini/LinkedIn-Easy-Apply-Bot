{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    gcc
    chromium
    chromedriver
    python312
    python312Packages.pip
    python312Packages.selenium
    python312Packages.webdriver-manager
    python312Packages.beautifulsoup4
    python312Packages.pandas
    python312Packages.pyautogui
    python312Packages.pyyaml
    python312Packages.lxml
    python312Packages.future
    python312Packages.python-dotenv
    python312Packages.packaging
  ];

  shellHook = ''
    export PATH=$PATH:${pkgs.chromedriver}/bin:${pkgs.chromium}/bin
    export CHROME_BIN=${pkgs.chromium}/bin/chromium
    export CHROMEDRIVER_PATH=${pkgs.chromedriver}/bin/chromedriver

    echo "✅ Nix environment ready with Chromium + Chromedriver."
    echo "🐍 Python version: $(python3 --version)"
    echo "🌐 Chromium version: $(${pkgs.chromium}/bin/chromium --version)"
    echo "🧩 Chromedriver: $(${pkgs.chromedriver}/bin/chromedriver --version)"
  '';
}
