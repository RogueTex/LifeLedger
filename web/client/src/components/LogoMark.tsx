import { motion } from "framer-motion";
import { Coins } from "lucide-react";

export default function LogoMark() {
  return (
    <motion.div
      className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-accent p-[1px] shadow-[0_0_15px_rgba(160,255,210,0.3)]"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
    >
      <motion.div
        className="w-full h-full bg-background/90 backdrop-blur-xl rounded-lg flex items-center justify-center relative overflow-hidden"
        animate={{ rotate: [0, 5, -5, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      >
        <Coins className="w-5 h-5 text-primary" />
        <motion.div
          className="absolute inset-0 rounded-lg"
          style={{ background: "radial-gradient(circle at center, rgba(160,255,210,0.3), transparent)" }}
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 3, repeat: Infinity }}
        />
      </motion.div>
    </motion.div>
  );
}
