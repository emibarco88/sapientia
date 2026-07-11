const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(
    "sapientia_token"
  );
}

export function setToken(
  token: string
): void {
  localStorage.setItem(
    "sapientia_token",
    token
  );
}

export function clearToken(): void {
  localStorage.removeItem(
    "sapientia_token"
  );
}

export async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const isFormData =
    typeof FormData !== "undefined" &&
    options.body instanceof FormData;

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,

      headers: {
        ...(
          !isFormData
            ? {
                "Content-Type":
                  "application/json",
              }
            : {}
        ),

        ...(
          token
            ? {
                Authorization:
                  `Bearer ${token}`,
              }
            : {}
        ),

        ...(options.headers || {}),
      },
    }
  );

  if (!response.ok) {
    let message =
      `API error: ${response.status}`;

    try {
      const payload =
        await response.json();

      message =
        payload.detail ||
        payload.message ||
        message;
    } catch {
      const responseText =
        await response.text();

      if (responseText) {
        message = responseText;
      }
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}