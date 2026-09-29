use database sod
--
-- Estructura de tabla para la tabla `users`
--

CREATE TABLE `users` (
  `UserID` varchar(50) NOT NULL,
  `Password` varchar(255) NOT NULL,
  `Type` int(11) NOT NULL,
  `Company` varchar(100) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Phone` varchar(20) NOT NULL,
  `active` bit(1) NOT NULL DEFAULT b'0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `users`
--

INSERT INTO `users` (`UserID`, `Password`, `Type`, `Company`, `Email`, `Phone`, `active`) VALUES
('ArturoRoa', '12345556', 0, 'Roandai', 'arb', '3', b'0'),
('Alex', 'Aiver@2025', 0, 'SOA', '', '', b'0'),
('Alex', 'scrypt:32768:8:1$a90uZHUrWcWuATdt$cf5c31208ca4e7d38f0c247800aa37405ea58bf34f8dc0e66d08cd72190f110ccf827f86583ba107e163569846a8416f6a31e72efdb269c3066132560a346306', 0, 'SOA', 'arodriguez@soa.com', '', b'1'),
('Aroa', 'scrypt:32768:8:1$MtQZeNwSgmKJC7CZ$3fd19315ef70fc0dcbb96fa108b5275198d745d6d349f6bcd1e62a3d35ae8927c0c0184354f58322a62c59e497e10a2101fd35f49276ff630f3b0d8cb096dc5a', 1, 'SOA', 'ar', '2', b'0'),
('a', 'scrypt:32768:8:1$tWZo1M3ftyk3Ssdn$f5a09ab77588dc5b10b2fbbcceb80d6adcfb235c076e8126acc7f6146248200fad399b912e1012a516892b824b8471c6521658ec5796d6d64391b60738e6583f', 2, 'SOA', 'a', '1', b'1'),
('david', 'scrypt:32768:8:1$XIxUyUPcK4odvDw8$2a4381a9d7dc2b781e78e31e14257d41da3606d668554de5e1a5b53a8e49b1958bfc3f779600fdf9217246f068ba7ff8d3d12affb219134f507d986dcc6fa5a9', 1, 'Roandai', 'Dave@roandai.com.mx', '2711659841', b'1'),
('aroasoa', 'scrypt:32768:8:1$zM4Nwxzh0RPasQXJ$0206bef2c7f1da4889d5e97d1c0378e2239d3411841f7073bf12b94d64354cec72f8b4a5113dff1377460241e7b9892ffdbd609bf97739eb930b30a32a3e803b', 1, 'SOADOS', 'aroa@soaprojects', '2721273166', b'1'),
('davo', 'scrypt:32768:8:1$ZwHfyNBrdxPXHaXb$ba9e7e71ee2e444cb13b09a080db2b5d5a246e7932d76c2ea96e82cd31c99d0622231c909d1878d69def951d9e66e89dfbf226e52541ed85e4e03a88513d4fd5', 1, 'Roandai', 'davo@gmail.com', '2711659841', b'1');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`Password`,`Email`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
