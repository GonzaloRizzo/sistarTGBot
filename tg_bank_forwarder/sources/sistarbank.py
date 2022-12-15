from tg_bank_forwarder.clients.SistarClient import SistarClient, SistarbankMovement


def sisterbank_source(username, password, title):
    def do_poll():
        c = SistarClient()
        c.login(username, password)

        items = c.movimientos()
        yield "sisterbank", items, SistarbankMovement, title

    return do_poll
