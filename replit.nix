{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.sqlite
  ];
  
  env = {
    PYTHONPATH = "/home/runner/${REPL_SLUG}";
    PORT = "3000";
  };
}
