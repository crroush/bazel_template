fn greeting() -> &'static str {
    "Hello, world from Rust!"
}

fn main() {
    println!("{}", greeting());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn greets_world() {
        assert_eq!(greeting(), "Hello, world from Rust!");
    }
}
