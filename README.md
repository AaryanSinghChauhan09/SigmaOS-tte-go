    # SigmaOS-tte-go

    Terminal text effects (Go flavour)

    Part of the **SigmaOS** sovereign operating-system ecosystem — a multi-repository
    distribution modelled on Linux Mint and Omarchy Linux. See the parent
    [`SigmaOS`](https://github.com/AaryanSinghChauhan09/SigmaOS) repository for the
    full component index.

    ## Upstream inspirations
    - https://github.com/omacom/tte-go

    ## Design principles applied
    - **Separation of Concerns**
- **Composability**
- **Fail-Fast**
- **Least Astonishment**
- **KISS**
- **Deterministic Testing**

    ## Usage
    Verbs: `effect, render, list, banner`

    ```
    $ sigma-tte effect box "hi"
┌────┐
│ hi │
└────┘
$ sigma-tte banner SIGMA
$ sigma-tte render "hi" --effects banner,box
$ sigma-tte list

    ```

    ## Build & test
    ```
    make build
    make test
    ```

    ## Licence
    GNU General Public License v3.0 (FOSS).
