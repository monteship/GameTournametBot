{ pkgs }: {
  deps = [
    pkgs.sudo
    pkgs.systemd
    pkgs.python310Full
    pkgs.replitPackages.stderred
    pkgs.scrapy
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.glib
      pkgs.xorg.libX11
    ];
    PYTHONHOME = "${pkgs.python310Full}";
    PYTHONBIN = "${pkgs.python310Full}/bin/python3.10";
    LANG = "en_US.UTF-8";
    STDERREDBIN = "${pkgs.replitPackages.stderred}/bin/stderred";
    PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar-python310}/bin/prybar-python310";
    PATH = "${pkgs.scrapy}/bin:${pkgs.python310Full}/bin:${pkgs.systemd}/bin:${pkgs.sudo}/bin:${pkgs.zlib}/bin:${pkgs.glib}/bin:${pkgs.xorg.libX11}/bin:${pkgs.replitPackages.stderred}/bin:${pkgs.replitPackages.prybar-python310}/bin:${pkgs.stdenv.cc.cc.lib}/bin:${pkgs.stdenv.cc.cc.lib}/sbin";
  };
}
