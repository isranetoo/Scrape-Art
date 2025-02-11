from bot_pje_trt2_scrapper import Bot_trt2_pje_scrape

if __name__ == "__main__":
    done = Bot_trt2_pje_scrape(assunto="Nubank",procs_por_pagina=20, max_paginas=5).run()