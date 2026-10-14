"use client";
import User from "@/app/model/user";
import {
	createContext,
	ReactNode,
	useContext,
	useEffect,
	useState,
	useMemo,
	useCallback,
} from "react";

type UserProp = User | undefined;

interface UserContextValue {
	user: UserProp;
	setUser: (user: UserProp) => void;
	refreshUser: () => void;
}

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
	const [user, setUser] = useState<UserProp>(undefined);

	const refreshUser = useCallback(() => {
		fetch(`${process.env.NEXT_PUBLIC_BASE_PATH}/profile/api`)
			.then((res) => res.json())
			.then((userData) => {
				if (userData) {
					setUser(userData);
				}
			})
			.catch(() => setUser(undefined));
	}, []);

	useEffect(() => {
		refreshUser();
	}, [refreshUser]);

	const value = useMemo(
		() => ({ user, setUser, refreshUser }),
		[user, refreshUser],
	);

	return (
		<UserContext.Provider value={value}>{children}</UserContext.Provider>
	);
}

export function useUser() {
	const context = useContext(UserContext);
	
	if (!context) throw new Error("useUser must be used within a UserProvider");
	return context;
}
