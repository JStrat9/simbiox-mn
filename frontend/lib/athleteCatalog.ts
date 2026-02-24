export type AthleteProfile = {
    name: string;
    avatarUrl: string;
};

const DEFAULT_ATHLETE_PROFILE: AthleteProfile = {
    name: "Cliente desconocido",
    avatarUrl: "",
};

export const ATHLETE_CATALOG: Record<string, AthleteProfile> = {
    athlete_1: { name: "Joan", avatarUrl: "/joan.jpg" },
    athlete_2: { name: "Luz", avatarUrl: "/avatars/luz.jpg" },
    athlete_3: { name: "Gabbi", avatarUrl: "/avatars/gabbi.jpg" },
    athlete_4: { name: "Sandra", avatarUrl: "/avatars/sandra.jpg" },
    athlete_5: { name: "Roc\u00edo", avatarUrl: "/avatars/rocio.jpg" },
    athlete_6: { name: "Sele", avatarUrl: "/avatars/sele.jpg" },
};

export function getAthleteProfile(athleteId: string): AthleteProfile {
    return ATHLETE_CATALOG[athleteId] ?? DEFAULT_ATHLETE_PROFILE;
}

export function getAthleteName(athleteId: string): string {
    return getAthleteProfile(athleteId).name;
}
