"use client";

import Script from "next/script";
import { useCallback, useRef } from "react";

interface CredentialResponse {
  credential: string;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: CredentialResponse) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

interface Props {
  onToken: (idToken: string) => void;
}

export default function GoogleSignInButton({ onToken }: Props) {
  const buttonRef = useRef<HTMLDivElement>(null);

  const init = useCallback(() => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId || !window.google || !buttonRef.current) return;
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => onToken(response.credential),
    });
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: "outline",
      size: "large",
      width: 300,
    });
  }, [onToken]);

  return (
    <>
      <Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" onLoad={init} onReady={init} />
      <div ref={buttonRef} />
    </>
  );
}
