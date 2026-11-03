import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID,
      clientSecret: process.env.AUTH_GITHUB_SECRET,
    }),
  ],
  callbacks: {
    signIn({ profile }) {
      const allowed = process.env.ALLOWED_GITHUB_USERNAME?.trim().toLowerCase();
      if (!allowed) {
        console.warn("Sign-in denied: ALLOWED_GITHUB_USERNAME is not set in environment.");
        return false;
      }
      const login = (profile as { login?: string })?.login?.toLowerCase();
      if (!login || login !== allowed) {
        console.warn(`Sign-in denied for GitHub user '${login}'. Expected '${allowed}'.`);
        return false;
      }
      return true;
    },
    jwt({ token, profile }) {
      if (profile) {
        token.username = (profile as { login?: string })?.login;
      }
      return token;
    },
    session({ session, token }) {
      if (session.user && token.username) {
        (session.user as { username?: string }).username = token.username as string;
      }
      return session;
    },
  },
});

