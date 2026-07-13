const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


const TOKEN_KEY =
  "sapientia_token";


export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(
    TOKEN_KEY
  );
}


export function setToken(
  token: string
): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.setItem(
    TOKEN_KEY,
    token
  );
}


export function clearToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(
    TOKEN_KEY
  );
}


function redirectToLogin(): void {
  if (typeof window === "undefined") {
    return;
  }

  const currentPath =
    window.location.pathname;

  if (currentPath !== "/") {
    window.location.replace("/");
  }
}


export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const isFormData =
    typeof FormData !== "undefined"
    && options.body instanceof FormData;

  const headers =
    new Headers(options.headers);

  if (!isFormData) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  let response: Response;

  try {
    response = await fetch(
      `${API_URL}${path}`,
      {
        ...options,
        headers,
      }
    );
  } catch (error) {
    throw new Error(
      "Unable to connect to the Sapientia API."
    );
  }

  if (
    response.status === 401
    || response.status === 403
  ) {
    clearToken();
    redirectToLogin();

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  if (!response.ok) {
    let message =
      `API error: ${response.status}`;

    try {
      const payload =
        await response.json();

      message =
        payload.detail
        || payload.message
        || message;
    } catch {
      try {
        const responseText =
          await response.text();

        if (responseText) {
          message = responseText;
        }
      } catch {
        // Preserve the default message.
      }
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null as T;
  }

  const contentType =
    response.headers.get(
      "content-type"
    );

  if (
    !contentType?.includes(
      "application/json"
    )
  ) {
    return null as T;
  }

  return response.json() as Promise<T>;
}