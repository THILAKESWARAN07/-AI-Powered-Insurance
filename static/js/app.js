async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function renderMessage(target, title, body, isError = false) {
  if (!target) return;
  target.classList.remove("hidden");
  target.innerHTML = `
    <h3>${title}</h3>
    <p style="color:${isError ? "#b42318" : "#157347"}">${body}</p>
  `;
}

(function initRegistration() {
  const form = document.getElementById("register-form");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    const output = document.getElementById("register-result");

    try {
      const result = await postJSON("/register", payload);
      renderMessage(
        output,
        "Registration complete",
        `Welcome ${result.user.name}. Next: compute risk, buy weekly plan, and monitor auto-claims. Your User ID is ${result.user.id}.`
      );

      output.innerHTML += `
        <div class="actions wrap">
          <a class="btn ghost" href="/dashboard?user_id=${result.user.id}">Open Dashboard</a>
          <a class="btn ghost" href="/plans?user_id=${result.user.id}">View Plan</a>
          <a class="btn ghost" href="/claims?user_id=${result.user.id}">View Claims</a>
          <a class="btn ghost" href="/calculate-risk?user_id=${result.user.id}" target="_blank">Calculate Risk (API)</a>
        </div>
      `;
    } catch (error) {
      renderMessage(output, "Registration failed", error.message, true);
    }
  });
})();

(function initBuyPlan() {
  const buttons = document.querySelectorAll("[data-buy-plan]");
  if (!buttons.length) return;

  buttons.forEach((button) => {
    button.addEventListener("click", async () => {
      const userId = button.getAttribute("data-buy-plan");
      const output = document.getElementById("plan-result") || document.getElementById("event-result");
      try {
        const result = await postJSON("/buy-plan", { user_id: userId });
        renderMessage(
          output,
          "Policy activated",
          `Weekly premium INR ${result.policy.weekly_premium_inr}, coverage INR ${result.policy.coverage_inr}.`
        );
      } catch (error) {
        renderMessage(output, "Plan activation failed", error.message, true);
      }
    });
  });
})();

(function initTriggers() {
  const triggerButtons = document.querySelectorAll("[data-trigger]");
  if (!triggerButtons.length) return;

  triggerButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const eventType = button.getAttribute("data-trigger");
      const userId = button.getAttribute("data-user");
      const output = document.getElementById("event-result") || document.getElementById("claim-live");

      try {
        const result = await postJSON("/trigger-event", {
          user_id: userId,
          event_type: eventType,
          gps_location: prompt("Mock GPS city (optional, leave blank for valid):") || "",
        });

        const claim = result.claim_result?.claim;
        if (claim) {
          renderMessage(
            output,
            "Trigger detected",
            `Claim ${claim.status}. Payout INR ${claim.payout_inr}. Trigger reason: ${result.trigger_reasons.join(", " )}.`
          );
        } else {
          renderMessage(output, "No Trigger", "No trigger condition met.");
        }
      } catch (error) {
        renderMessage(output, "Trigger failed", error.message, true);
      }
    });
  });
})();

(function initClaimRefresh() {
  const refresh = document.querySelector("[data-refresh-claim]");
  if (!refresh) return;

  refresh.addEventListener("click", async () => {
    const userId = refresh.getAttribute("data-refresh-claim");
    const output = document.getElementById("claim-live");
    try {
      const response = await fetch(`/claim?user_id=${userId}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not fetch claims");

      if (data.latest_claim) {
        renderMessage(
          output,
          "Latest claim",
          `Status: ${data.latest_claim.status}, Payout: INR ${data.latest_claim.payout_inr}, Event: ${data.latest_claim.event_type}`
        );
      } else {
        renderMessage(output, "No claims yet", "Trigger an event to auto-generate claim.");
      }
    } catch (error) {
      renderMessage(output, "Claim fetch failed", error.message, true);
    }
  });
})();
