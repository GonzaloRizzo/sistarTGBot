import puppeteer from 'puppeteer';
import Fastify from 'fastify'

const browser = await puppeteer.launch({
  headless: "new", args: [
    '--no-sandbox',
    '--disable-setuid-sandbox'
  ]
});
const fastify = Fastify({
  logger: true
})


const getCookie = (cookies, name) =>
  cookies.filter(c => c.name === name)[0].value


fastify.get("/", async function handler(request, reply) {
  return { ok: true }
})

fastify.get("/login", async function handler(request, reply) {
  const page = await browser.newPage();

  await page.goto('https://www.itau.com.uy/inst/');
  await page.click("#js-open-login")


  await page.type('#documento', process.env.ITAU_ID);
  await page.type('#pass', process.env.ITAU_PASS);
  await page.click('#vprocesar');

  await page.waitForNavigation();


  const cookies = await page.cookies();

  const ret = {
    cookies: {
      TS01888778: getCookie(cookies, "TS01888778"),
      JSESSIONID: getCookie(cookies, "JSESSIONID"),
    }
  }

  await page.close()

  return ret
})
try {
  await fastify.listen({ port: 3000, host: "0.0.0.0" })
} catch (err) {
  fastify.log.error(err)
  process.exit(1)
}




