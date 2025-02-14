
from bot_pje_trt2_juris import Bot_trt2_pje_juris

if __name__ == "__main__":
    done = Bot_trt2_pje_juris(assunto="Itau",procs_por_pagina= 20, max_paginas=15).run()