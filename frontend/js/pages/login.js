// Login page

export function page() {
  return `
  <div class="login-card">
    <div class="login-logo">🌴 Oasis</div>
    <div class="login-sub">Smart Desert Orchard Management</div>
    <form id="login-form">
      <label for="email">Email</label>
      <input id="email" name="email" type="email" autocomplete="email" required value="demo@oasis.farm" />
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required value="demo1234" />
      <div style="margin-top:16px" class="vstack">
        <button class="btn" type="submit">Sign in</button>
        <button class="btn secondary" type="button" id="demo-btn">Use demo account</button>
      </div>
    </form>
  </div>`;
}