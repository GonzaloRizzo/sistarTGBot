from tg_bank_forwarder.clients.SistarClient import SistarClient, SistarbankMovement


def sisterbank_source(username, password):
    def do_poll():
        c = SistarClient()
        c.login(username, password)

        items = c.movimientos()
        yield "sisterbank", items, SistarbankMovement

    return do_poll
