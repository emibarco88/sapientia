import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

type SharedProps = {
  children: ReactNode;
  className?: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
};

type LinkButtonProps = SharedProps & {
  href: string;
  onClick?: never;
  type?: never;
};

type NativeButtonProps = SharedProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    href?: never;
  };

type ButtonProps = LinkButtonProps | NativeButtonProps;

export default function Button(props: ButtonProps) {
  const {
    children,
    className = "",
    variant = "primary",
    size = "md",
    leadingIcon,
    trailingIcon,
  } = props;

  const classes = [
    "sap-button",
    `sap-button-${variant}`,
    size !== "md" ? `sap-button-${size}` : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const content = (
    <>
      {leadingIcon}
      <span>{children}</span>
      {trailingIcon}
    </>
  );

  if ("href" in props && props.href) {
    return (
      <Link className={classes} href={props.href}>
        {content}
      </Link>
    );
  }

  const {
    href: _href,
    leadingIcon: _leadingIcon,
    trailingIcon: _trailingIcon,
    variant: _variant,
    size: _size,
    ...buttonProps
  } = props as NativeButtonProps;

  return (
    <button className={classes} {...buttonProps}>
      {content}
    </button>
  );
}
