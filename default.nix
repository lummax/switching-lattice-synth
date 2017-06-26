with import <nixpkgs> {};

let
  ppackages = python35Packages;

  espresso = stdenv.mkDerivation rec {
    name = "espresso-ab-1.0";
    src = fetchurl {
      url = "https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/eqntott/espresso-ab-1.0.tar.gz";
      sha256 = "0yalzmdm2w385zz2wijqj3a29qrv0jk7s9lc2cg3gf2q8av4g2kq";
    };
    buildPhase = ''make || make CFLAGS=-ansi'';
  };

  pyeda = ppackages.buildPythonPackage rec {
    name = "pyeda-${version}";
    version = "0.28.0";

    src = pkgs.fetchurl{
      url = "https://github.com/cjdrake/pyeda/archive/v${version}.tar.gz";
      sha256 = "08pzwlfc5m5rz2s5v47fan444635bd70w08lsqddl0d09blfgvdi";
    };
    buildInputs = [ espresso picosat ppackages.nose ];
  };

  cryptominisat = stdenv.mkDerivation rec {
    name = "cryptominisat-${version}";
    version = "5.0.1";

    src = fetchurl {
      url = "https://github.com/msoos/cryptominisat/archive/${version}.tar.gz";
      sha256 = "0qz2llq8l5y6slgshwiq1f72cjrpbs1vvqg4907r3mfb1v4m77bq";
    };
    # vim is needed for `xxd`
    buildInputs = [ cmake vim boost ];
  };

  python-cryptominisat = ppackages.buildPythonPackage rec {
    name = "python-cryptominisat-${version}";
    version = "0.1-501";

    src = fetchgit {
      url = "https://github.com/lummax/python-cryptominisat.git";
      rev = "6896e3e9445ed6cf70339bef16919f0dd18cf4c4";
      sha256 = "1yv1x3a3rwwmgb3jnii8567ds7lhlp1wqkb9sqcwx3xx56fwkz5x";
    };
    buildInputs = [ cryptominisat ppackages.cython ];
  };

  depqbf = stdenv.mkDerivation rec {
    name = "depqbf-${version}";
    version = "6.01";

    src = fetchurl {
      url = "https://github.com/lonsing/depqbf/archive/version-${version}.tar.gz";
      sha256 = "0wwx21qik7i1jvdkb4fpac2zgjxqbnz3c8qp7iikkh0wc4ycxxp1";
    };

    buildInputs = [ stdenv.cc.libc stdenv.cc.libc.static wget ];
    patchPhase = ''
        sed -i 's:/bin/bash:/usr/bin/env bash:' compile.sh
    '';
    buildPhase = ''
        ./compile.sh nobloqqer
    '';
    installPhase = ''
        mkdir -p "$out/bin"
        cp depqbf "$out/bin"
    '';
  };

  rareqs = stdenv.mkDerivation rec {
    name = "rareqs-${version}";
    version = "1.1";

    src = fetchurl {
      url = "http://sat.inesc-id.pt/~mikolas/sw/areqs/rareqs-${version}.src.tgz";
      sha256 = "18z2j68nqzcixp3nscr4si5rwrdswqa5kjr2x5mh64z8jishjn1d";
    };

    buildInputs = [ zlib ];

    installPhase = ''
        mkdir -p "$out/bin"
        cp rareqs "$out/bin"
    '';
  };

  hypothesis = ppackages.buildPythonPackage rec {
    name = "hypothesis-${version}";
    version = "3.7.0";

    src = pkgs.fetchurl{
      url = "https://github.com/HypothesisWorks/hypothesis-python/archive/${version}.tar.gz";
      sha256 = "1y91cpn30bal5chfvmvm3v9n48ryaclk8anpplxnhq8i7d4ipgki";
    };
    doCheck = false;
  };

  bloqqer = stdenv.mkDerivation rec {
    name = "bloqqer";
    version = "037";
    src = fetchurl {
      url = "http://fmv.jku.at/bloqqer/bloqqer-037-8660cb9-151127.tar.gz";
      sha256 = "10z2bc7s522k56q6yy6g7xl9rw19bza2kv905mvj7swixcvda92i";
    };
    dontAddPrefix = true;
    installPhase = ''
      mkdir -p $out/bin
      cp bloqqer $out/bin
    '';
  };

  minisolvers = stdenv.mkDerivation rec {
    name = "minisolvers-${version}";
    version = "git";

    src = fetchgit {
      url = "https://github.com/liffiton/PyMiniSolvers.git";
      rev = "9c24bb632d";
      sha256 = "1gg4r5gdhhx18v742lf5rwrgi8cn7d7a0vy5yw4ilv8nznvp6h3h";
    };

    buildInputs = [ zlib python3 ];
    doCheck = true;
    checkTarget = "test";

    installPhase = ''
      mkdir -p $out/lib/python3.5/site-packages
      cp -v *.py $out/lib/python3.5/site-packages
      cp -v *.so $out/lib/python3.5/site-packages
    '';
  };

in rec {
  dev = stdenv.mkDerivation rec {
    name = "dev";
    buildInputs = [ python3 pyeda python-cryptominisat
                    minisolvers hypothesis cryptominisat
                    minisat depqbf rareqs bloqqer ];
  };
}
