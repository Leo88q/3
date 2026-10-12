import { test, expect } from "@playwright/test";
test("start, delivery, pause, result, persistence and cosmetics", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.clock.install();
  await page.goto("/");
  await page.getByRole("button", { name: "Отправиться в рейс" }).click();
  const rect = await page.locator("canvas").boundingBox();
  await page.mouse.click(
    rect.x + rect.width * 0.23,
    rect.y + rect.height * 0.25,
  );
  await expect(page.locator("#score")).toHaveText("0100");
  await page.locator("#pause").click();
  const time = await page.locator("#time").textContent();
  await page.clock.runFor(3000);
  await expect(page.locator("#time")).toHaveText(time);
  await page.getByRole("button", { name: "Продолжить" }).click();
  await page.clock.runFor(91000);
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator("#coins")).toHaveText("1");
  await page.reload();
  await expect(page.locator("#best")).toHaveText("100");
  await page.getByRole("button", { name: "Моя лодка" }).click();
  await expect(page.locator('[data-skin="sunset"]')).toBeDisabled();
  expect(errors).toEqual([]);
});
test("mobile layout fits and cosmetics persist", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.evaluate(() =>
    localStorage.setItem(
      "noriwake-save",
      JSON.stringify({
        coins: 100,
        best: 0,
        runs: 0,
        owned: ["mint"],
        skin: "mint",
      }),
    ),
  );
  await page.reload();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.getByRole("button", { name: "Моя лодка" }).click();
  await page.locator('[data-skin="sunset"]').click();
  await expect(page.locator('[data-skin="sunset"]')).toHaveText("Выбрано");
  await page.reload();
  await expect(page.locator("#coins")).toHaveText("20");
  await page.screenshot({ path: "test-results/noriwake-mobile.png" });
});
